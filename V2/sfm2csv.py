import sys
import pandas as pd
import numpy as np
import getopt
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage : sfm2csv.py <inputfile> <outputfile>")

    inputfile = sys.argv[1]
    outputfile = sys.argv[2]

    with open(inputfile) as f:
        sfm = load(f, Loader=Loader)

    # Getting gps data from exif tags
    d = []
    for view in sfm['views']:
        d.append({
            'path': view['path'].split(sep='/')[-1],
            'poseId': int(view['poseId']),
            'gpsAltitude': float(view['metadata']['GPS:Altitude']),
            'gpsAltitudeRef': float(view['metadata']['GPS:AltitudeRef']),
            'gpsLatitude': view['metadata']['GPS:Latitude'],
            'gpsLatitudeRef': view['metadata']['GPS:LatitudeRef'],
            'gpsLongitude': view['metadata']['GPS:Longitude'],
            'gpsLongitudeRef': view['metadata']['GPS:LongitudeRef']
        })
    df = pd.DataFrame(d)

    # Some cleaning up
    df['gpsLatitude'] = df.apply(
        lambda row: row['gpsLatitude'].replace(',', ' '), axis=1)
    df['gpsLongitude'] = df.apply(
        lambda row: row['gpsLongitude'].replace(',', ' '), axis=1)

    # Adding the conversion from degree, minute, seconde to decimal degree
    def dms2dec(dms, ref):
        s = dms.split()
        o = float(s[0]) + float(s[1])*1/60 + float(s[2])*1/3600
        if (ref == "W" or ref == "S"):
            return -o
        else:
            return o
    df['gpsDecLatitude'] = df.apply(lambda row: dms2dec(
        row['gpsLatitude'], row['gpsLatitudeRef']), axis=1)
    df['gpsDecLongitude'] = df.apply(lambda row: dms2dec(
        row['gpsLongitude'], row['gpsLongitudeRef']), axis=1)

    # Getting poses coordinates 2 -0 -1
    df['x'] = np.nan
    df['y'] = np.nan
    df['z'] = np.nan
    for pose in sfm['poses']:
        df.loc[df['poseId'] == int(pose['poseId']), ['x', 'y', 'z']] = [
            float(pose['pose']['transform']['center'][0]),
            float(pose['pose']['transform']['center'][1]),
            float(pose['pose']['transform']['center'][2])
        ]

    df.to_csv(outputfile, index=False)
