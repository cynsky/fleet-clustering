import numpy as np


def create_lonlat_array(df, valid_ssvid):
    """
    Unlabelled rows are 0 (either because vessel
    no broadcasting on day or not grouped)
    
    Other rows are +1 for cluster and -1 elsewhere
    """
    n_ssvid = len(valid_ssvid)
    ssvid_map = {ssvid : i for (i, ssvid) in enumerate(df.ssvid)}
    lonlats = df[['lon', 'lat']].values
    C = np.empty([n_ssvid, 2])
    C.fill(np.nan)
    for i, ssvid in enumerate(valid_ssvid):
        if ssvid not in ssvid_map:
            continue
        j = ssvid_map[ssvid]
        C[i, :] = lonlats[j]
    return C

def create_composite_lonlat_array(df_by_date, valid_ssvid):
    Cns = []
    for date in sorted(df_by_date):
        Cns.append(create_lonlat_array(df_by_date[date], valid_ssvid))
    return np.concatenate(Cns, axis=1)

def compute_distances_by_date(C):
    # Compute the distances, ignoring infs
    AVG_EARTH_RADIUS = 6371  # in km
    n = len(C)
    m = C.shape[1] // 2
    assert C.shape[1] % 2 == 0
    distances = np.zeros([n, n, m])
    Cr = np.radians(C)
    for i in range(n):
        for j in range(0, m):
            lat1 = Cr[i, None, 2 * j + 1]
            lat2 = Cr[:, 2 * j + 1]
            lng1 = Cr[i, None, 2 * j]
            lng2 = Cr[:, 2 * j]
            lat = lat2 - lat1
            lng = lng2 - lng1
            d = np.sin(lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(lng / 2) ** 2
            h = 2 * AVG_EARTH_RADIUS * np.arcsin(np.sqrt(d))
            distances[i, :, j] = h
    distances[np.isnan(distances)] = np.inf
    return distances

def compute_distances_tweaked(C, gamma=2, min_clip=1, max_clip=np.inf):
    # Compute the distances, ignoring infs
    assert min_clip > 0
    AVG_EARTH_RADIUS = 6371  # in km
    n = len(C)
    m = C.shape[1] // 2
    distances = np.zeros([n, n])
    Cr = np.radians(C)
    Cr_mask = np.isinf(Cr) 
    Crm = Cr.copy()
    Crm[Cr_mask] = 0
    for i in range(n):
        ds = np.zeros([n, m])
        for j in range(0, m):
            lat1 = Crm[i, None, 2 * j + 1]
            lat2 = Crm[:, 2 * j + 1]
            lng1 = Crm[i, None, 2 * j]
            lng2 = Crm[:, 2 * j]
            lat = lat2 - lat1
            lng = lng2 - lng1
            d = np.sin(lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(lng / 2) ** 2
            h = 2 * AVG_EARTH_RADIUS * np.arcsin(np.sqrt(d))
            h = np.clip(h, min_clip, max_clip)
            ds[:, j] = h
        # Replace any nans with infs so we can sort them out of the way
        mask = np.isnan(ds)
        ds[mask] = np.inf
        ds.sort(axis=1)
        # Make a new mask indicating good data.
        mask = ~np.isinf(ds)
        weights = np.linspace(1, 0, ds.shape[1]) ** gamma #np.exp(-0.5 * (np.arange(d2s.shape[1]) / float(days)) ** 2)
        assert not np.isnan(weights).sum()
        assert weights.sum() > 0
        for j in range(n):
            submask = mask[j]
            subweights = weights[submask]
            norm = subweights.sum()
            if norm == 0:
                d = np.inf
            else:
                d = np.exp((np.log(ds[j, submask]) * subweights).sum() / norm)
                assert not np.isnan(d)
            distances[i, j] = d 
    distances[np.isnan(distances)] = np.inf
    return distances

# For backward compatibility
compute_distances_4 = compute_distances_tweaked

def compute_distances_RMS(C, gamma=2, min_clip=1, max_clip=np.inf):
    # Compute the distances, ignoring infs
    assert min_clip > 0
    AVG_EARTH_RADIUS = 6371  # in km
    n = len(C)
    m = C.shape[1] // 2
    distances = np.zeros([n, n])
    Cr = np.radians(C)
    Cr_mask = np.isinf(Cr) 
    Crm = Cr.copy()
    Crm[Cr_mask] = 0
    for i in range(n):
        ds = np.zeros([n, m])
        for j in range(0, m):
            lat1 = Crm[i, None, 2 * j + 1]
            lat2 = Crm[:, 2 * j + 1]
            lng1 = Crm[i, None, 2 * j]
            lng2 = Crm[:, 2 * j]
            lat = lat2 - lat1
            lng = lng2 - lng1
            d = np.sin(lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(lng / 2) ** 2
            h = 2 * AVG_EARTH_RADIUS * np.arcsin(np.sqrt(d))
            h = np.clip(h, min_clip, max_clip)
            ds[:, j] = h
        # Replace any nans with infs so we can sort them out of the way
        mask = np.isnan(ds)
        ds[mask] = np.inf
        ds.sort(axis=1)
        # Make a new mask indicating good data.
        mask = ~np.isinf(ds)
        for j in range(n):
            submask = mask[j]
            if submask.sum() == 0:
                d = np.inf
            else:
                d = ds[j, submask].mean()
                assert not np.isnan(d)
            distances[i, j] = d 
    distances[np.isnan(distances)] = np.inf
    return distances


def infclip(X, v):
    Y = np.minimum(X, v)
    Y[np.isinf(X)] = np.inf
    return Y
