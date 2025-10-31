# Docker

This project provides a Dockerfile to build and run the application in a container.

## Building the image

To build the image, you can use the `make build` command from the `docker` folder. This will build the image with the name `unicef/hope-beneficiary-portal:local`.

```shell
cd docker
make build
```

## Running the image

To run the image, you can use the `make run` command from the `docker` folder. This will run the image and expose the port 8000.

```shell
cd docker
make run
```

## Checking the image

To check the image, you can use the `make check` command from the `docker` folder. This will run the `check.sh` script inside the container.

```shell
cd docker
make check
```

## Shell

To get a shell inside the container, you can use the `make shell` command from the `docker` folder.

```shell
cd docker
make shell
```
