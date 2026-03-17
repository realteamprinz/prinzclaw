#!/bin/bash
cd "$(dirname "$0")"
node --import tsx ./bin/prinzclaw "$@"
