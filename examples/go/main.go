package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"golang.org/x/oauth2"
)

var gatewayPath = regexp.MustCompile(`^/gateway/[^/]+/mcp$`)

// The MCP SDK uses OAuthHandler for Bearer headers, including a static API key.
// This avoids adding Authorization in a custom http.RoundTripper.
type staticBearer struct{ key string }

func (b staticBearer) TokenSource(context.Context) (oauth2.TokenSource, error) {
	return oauth2.StaticTokenSource(&oauth2.Token{AccessToken: b.key, TokenType: "Bearer"}), nil
}

func (b staticBearer) Authorize(_ context.Context, _ *http.Request, response *http.Response) error {
	if response != nil && response.Body != nil {
		response.Body.Close()
	}
	return errors.New("Mithrandir rejected the key; check the gateway ID, key and access scope")
}

func gatewayURL(raw string) (string, error) {
	u, err := url.Parse(raw)
	if err != nil || u == nil {
		return "", errors.New("set MITHRANDIR_GATEWAY_URL to the issued /gateway/<id>/mcp URL")
	}
	local := u.Hostname() == "localhost" || u.Hostname() == "127.0.0.1" || u.Hostname() == "::1"
	if (u.Scheme != "https" && !(local && u.Scheme == "http")) || u.Host == "" ||
		u.User != nil || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" ||
		!gatewayPath.MatchString(u.Path) {
		return "", errors.New("use the issued HTTPS /gateway/<id>/mcp URL without credentials or query parameters")
	}
	return u.String(), nil
}

func run() error {
	endpoint, err := gatewayURL(os.Getenv("MITHRANDIR_GATEWAY_URL"))
	if err != nil {
		return err
	}
	key := os.Getenv("MITHRANDIR_API_KEY")
	if key == "" || strings.ContainsAny(key, "\r\n") {
		return errors.New("set MITHRANDIR_API_KEY to your Mithrandir account or bound client key")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	client := mcp.NewClient(&mcp.Implementation{Name: "mithrandir-go-example", Version: "1.0.0"}, nil)
	transport := &mcp.StreamableClientTransport{
		Endpoint:             endpoint,
		OAuthHandler:         staticBearer{key},
		DisableStandaloneSSE: true, // This sample only needs request/response POSTs.
	}
	session, err := client.Connect(ctx, transport, nil)
	if err != nil {
		return fmt.Errorf("connect: %w", err)
	}
	defer session.Close()

	names := []string{}
	for tool, err := range session.Tools(ctx, nil) {
		if err != nil {
			return fmt.Errorf("list tools: %w", err)
		}
		names = append(names, tool.Name)
	}
	output := map[string]any{"connected": true, "tools": names}

	// A tool call is opt-in because upstream tools may be effectful or billable.
	if name := os.Getenv("MCP_TOOL"); name != "" {
		advertised := false
		for _, toolName := range names {
			if toolName == name {
				advertised = true
				break
			}
		}
		if !advertised {
			return fmt.Errorf("tool %q was not advertised by this gateway", name)
		}
		argsJSON := os.Getenv("MCP_ARGS_JSON")
		if argsJSON == "" {
			argsJSON = "{}"
		}
		var args map[string]any
		if err := json.Unmarshal([]byte(argsJSON), &args); err != nil || args == nil {
			return errors.New("MCP_ARGS_JSON must be a JSON object")
		}
		result, err := session.CallTool(ctx, &mcp.CallToolParams{Name: name, Arguments: args})
		if err != nil {
			return fmt.Errorf("call tool: %w", err)
		}
		output["call"] = result
	}
	encoded, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return err
	}
	fmt.Println(string(encoded))
	return nil
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "Mithrandir connection failed:", err)
		os.Exit(1)
	}
}
