#!/bin/sh

curl -i -H "Accept: application/json" -X POST -d @test-payload.json http://127.0.0.1:4020/
