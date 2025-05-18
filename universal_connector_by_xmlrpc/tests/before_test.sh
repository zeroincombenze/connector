#!/bin/bash

for port in 8167 8168; do
  for ctr in {11..0}; do
      ss -lt|grep 0.0.0.0:$port
      [[ $? -eq 0 ]] && break
      [[ $port -ge 8200 ]] && vid="oca$((port-8260))" || vid="odoo$((port-8160))"
      echo "No Odoo instance running found at port $port ($vid)"
      echo odooctl restart $vid
      odooctl restart $vid
      sleep 5
  done
  [[ $ctr -eq 0 ]] && exit 1
done
[[ $ctr -eq 0 ]] && exit 1
msg=""
psql -Atl|grep -E "^demo7\|" || msg="$msg DB demo7 not found!"
psql -Atl|grep -E "^demo8\|" || msg="$msg DB demo8 not found!"
[[ -n $msg ]] && echo $msg && exit 1
exit 0
