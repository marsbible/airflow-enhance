#!/bin/bash

for i in `ls *.pid`
do
  kill `cat $i`
done

