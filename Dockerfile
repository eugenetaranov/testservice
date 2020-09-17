FROM golang:1.14-alpine AS build

WORKDIR /src/
COPY	src /src/
RUN	CGO_ENABLED=0 go build -o /bin/testservice

FROM	alpine:latest
COPY	--from=build /bin/testservice /bin/testservice
EXPOSE 	8080/tcp
RUN	adduser -DS app
USER	app
ENTRYPOINT ["/bin/testservice"]
