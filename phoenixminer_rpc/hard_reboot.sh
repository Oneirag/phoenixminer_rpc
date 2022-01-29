# Activate sysrq
echo "1" > /proc/sys/kernel/sysrq

# Sync disks
echo "s" > /proc/sysrq-trigger
/bin/sleep 1

# Remount all disks read-only.
echo "u" > /proc/sysrq-trigger
/bin/sleep 1

# Issue the hard reboot command.
echo "b" > /proc/sysrq-trigger
