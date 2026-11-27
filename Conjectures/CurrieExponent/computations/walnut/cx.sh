#!/bin/bash
# usage: cx.sh WORD  -> Walnut commands proving factor complexity 2n+1 for WORD (ternary)
X=$1
cat <<EOT
def ${X}fe "?msd_gam At t<n => ${X}[i+t]=${X}[j+t]":
def ${X}e0 "?msd_gam Ej \$${X}fe(i,j,n) & ${X}[j+n]=@0":
def ${X}e1 "?msd_gam Ej \$${X}fe(i,j,n) & ${X}[j+n]=@1":
def ${X}e2 "?msd_gam Ej \$${X}fe(i,j,n) & ${X}[j+n]=@2":
def ${X}r3 "?msd_gam \$${X}e0(i,n) & \$${X}e1(i,n) & \$${X}e2(i,n)":
def ${X}rs "?msd_gam (\$${X}e0(i,n) & \$${X}e1(i,n)) | (\$${X}e0(i,n) & \$${X}e2(i,n)) | (\$${X}e1(i,n) & \$${X}e2(i,n))":
def ${X}one3 "?msd_gam (Ei \$${X}r3(i,n)) & Ai,j (\$${X}rs(i,n) & \$${X}rs(j,n)) => \$${X}fe(i,j,n)":
def ${X}two2 "?msd_gam (~Ei \$${X}r3(i,n)) & (Ei,j \$${X}rs(i,n) & \$${X}rs(j,n) & ~\$${X}fe(i,j,n)) & Ai,j,k (\$${X}rs(i,n) & \$${X}rs(j,n) & \$${X}rs(k,n)) => (\$${X}fe(i,j,n) | \$${X}fe(i,k,n) | \$${X}fe(j,k,n))":
eval ${X}cx "?msd_gam An \$${X}one3(n) | \$${X}two2(n)":
EOT
