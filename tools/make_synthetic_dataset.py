"""SMOKE-TEST ONLY: fake CSV shaped like NATICUSdroid (86 permission columns + 'Result').
Results on this data mean nothing about real malware detection."""
import numpy as np, pandas as pd
from isoline.schema import FEATURE_PERMISSIONS as F

rng = np.random.default_rng(0)
cols = F[:80] + ["com.google.android.providers.gsf.permission.READ_GSERVICES",
                 "com.android.launcher.permission.READ_SETTINGS"] + [f"custom.perm.X{i}" for i in range(4)]
n = 3000
y = rng.integers(0, 2, n)
X = (rng.random((n, len(cols))) < rng.random(len(cols)) * 0.3).astype(int)
for name in ("READ_SMS", "SEND_SMS", "RECEIVE_BOOT_COMPLETED", "SYSTEM_ALERT_WINDOW"):
    i = cols.index("android.permission." + name)
    X[:, i] = np.where(y == 1, rng.random(n) < 0.6, rng.random(n) < 0.1).astype(int)
df = pd.DataFrame(X, columns=cols); df["Result"] = y
df.to_csv("synthetic.csv", index=False); print("wrote synthetic.csv", df.shape)
