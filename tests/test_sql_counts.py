import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv('my-node-app/.env')
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    port=int(os.getenv('DB_PORT', 4000)),
    ssl_verify_cert=True,
    ssl_verify_identity=True
)
cur = conn.cursor(dictionary=True)
cur.execute('''
    SELECT
        COUNT(*) as total_bikes,
        SUM(CASE WHEN (isSoldout = 1 OR status IN ('sold', 'soldout') OR listing_status IN ('sold', 'soldout'))
            THEN 1 ELSE 0 END) as sold_bikes,
        SUM(CASE WHEN (isSoldout IS NULL OR isSoldout = 0) AND status NOT IN ('sold', 'soldout') AND listing_status NOT IN ('sold', 'soldout')
                      AND (status = 'rejected' OR listing_status = 'rejected')
            THEN 1 ELSE 0 END) as rejected_bikes,
        SUM(CASE WHEN (isSoldout IS NULL OR isSoldout = 0) AND status NOT IN ('sold', 'soldout') AND listing_status NOT IN ('sold', 'soldout')
                      AND (status != 'rejected' AND listing_status != 'rejected')
                      AND (status = 'pending' OR listing_status = 'pending')
            THEN 1 ELSE 0 END) as pending_bikes,
        SUM(CASE WHEN (isSoldout IS NULL OR isSoldout = 0) AND status NOT IN ('sold', 'soldout') AND listing_status NOT IN ('sold', 'soldout')
                      AND (status != 'rejected' AND listing_status != 'rejected')
                      AND (status != 'pending' AND listing_status != 'pending')
                      AND (status IN ('approved', 'published') OR listing_status IN ('approved', 'published'))
            THEN 1 ELSE 0 END) as approved_bikes
    FROM bikes
    WHERE COALESCE(status, '') != 'archived' AND COALESCE(listing_status, '') != 'archived'
''')
row = cur.fetchone()
print('Accurate mutually-exclusive counts:', row)
cur.close()
conn.close()
