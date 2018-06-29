#!/bin/bash
wget `curl -s https://api.github.com/repos/openscap/scap-security-guide/releases/latest | jq -r ".assets[] | select(.name | test(\"(scap-security-guide-[0-9].[0-9].[0-9]*).zip\")) | .browser_download_url"` -O ssg.zip

