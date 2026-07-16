package api

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestMalformedBodyReturnsBadRequest(t *testing.T) {
	request := httptest.NewRequest(http.MethodPost, "/items", strings.NewReader("{"))
	response := httptest.NewRecorder()

	NewHandler(func() string { return "request-123" }).ServeHTTP(response, request)

	if response.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", response.Code, http.StatusBadRequest)
	}
	if response.Body.String() != "invalid request\n" {
		t.Fatalf("body = %q", response.Body.String())
	}
}
