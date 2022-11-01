#!/bin/bash

for i in {1..60}
do
   echo $(date +%F_%T) ${i}
   sleep 1
done
