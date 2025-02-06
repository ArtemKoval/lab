#!/bin/bash

ASPNETCORE_ENVIRONMENT=Development

dotnet build

dotnet run ./bin/Debug/netcoreapp2.1/Web.dll