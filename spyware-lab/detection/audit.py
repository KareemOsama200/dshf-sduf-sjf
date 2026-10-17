import re, subprocess, sys

DANGEROUS = {
    "android.permission.READ_CALL_LOG": 5,
    "android.permission.READ_CONTACTS": 5,
    "android.permission.READ_SMS": 5,
    "android.permission.RECORD_AUDIO": 4,
    "android.permission.ACCESS_FINE_LOCATION": 4,
    "android.permission.READ_EXTERNAL_STORAGE": 3,
    "android.permission.SYSTEM_ALERT_WINDOW": 3,
    "android.permission.RECEIVE_BOOT_COMPLETED": 3,
}

def main():
    r = subprocess.run(["adb", "shell", "dumpsys", "package"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("adb not connected — start the emulator first")

    blocks = re.split(r"\n\s+Package \[", r.stdout)
    findings = []
    for b in blocks[1:]:
        name = b.split("]")[0]
        granted = set(re.findall(r"(android\.permission\.[\w.]+): granted=true", b))
        hits = granted & DANGEROUS.keys()
        if hits:
            score = sum(DANGEROUS[h] for h in hits)
            findings.append((score, name, sorted(hits)))

    findings.sort(reverse=True)
    print(f"{'SCORE':<6} {'PACKAGE'}")
    print("-" * 60)
    for score, name, hits in findings:
        print(f"{score:<6} {name}")
        for h in hits:
            print(f"       └─ {h}")
    if not findings:
        print("no packages with dangerous permission combos found")

if __name__ == "__main__":
    main()
