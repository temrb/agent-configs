package api

import (
	"net/http"
)

func NewHandler(nextID func() string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			w.Header().Set("X-Request-ID", nextID())
			return
		}

		w.WriteHeader(http.StatusBadRequest)
		w.Header().Set("X-Request-ID", nextID())
		_, _ = w.Write([]byte("invalid request\n"))
	})
}
