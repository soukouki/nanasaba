#!/bin/bash

cd $(dirname $0)

set -a
source ./.env

ruby managebot.rb | tee -a managebot.log
