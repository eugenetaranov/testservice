package main

import (
	"fmt"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

func main() {
	serviceName, _ := os.LookupEnv("NAME")
	hostname, _ := os.Hostname()

	gin.SetMode(gin.ReleaseMode)
	gin.DisableConsoleColor()
	r := gin.Default()

	r.GET("/healthz", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{}) })
	r.GET("/", func(c *gin.Context) {
		c.Data(
			http.StatusOK,
			"text/plain",
			[]byte(fmt.Sprintf("Service %s\nHost %s\n", serviceName, hostname)),
		)
	})

	r.Run(":8080")
}
