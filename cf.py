# # import requests

# # url = "https://www.cfbenchmarks.com/api/v1/history/values"

# # payload = {}
# # headers = {
# #   'Accept': 'application/json',
# #   'Authorization': 'Basic PHVzZXJuYW1lPjo8cGFzc3dvcmQ+'
# # }

# # response = requests.request("GET", url, headers=headers, data=payload)

# # print(response.text)

# import http.client

# conn = http.client.HTTPSConnection("www.cfbenchmarks.com")
# payload = ''
# headers = {
#   'Accept': 'application/json',
#   'Authorization': 'Basic PHVzZXJuYW1lPjo8cGFzc3dvcmQ+'
# }
# conn.request("GET", "/api/v1/history/values", payload, headers)
# res = conn.getresponse()
# data = res.read()
# print(data.decode("utf-8"))


# (Kalshi
#  )

certhelp2026@gmail.com

# d6b36e61-f8b2-4b5b-86ae-dfba7da1c799

# -----BEGIN RSA PRIVATE KEY-----
# MIIEowIBAAKCAQEA0LFM0XPZ5MNBD2upT6CcfstgTE6pP6vIsCI7LZRINxucOUG/
# 6d7vIp+PUWN8Qd2NmcaJSPPVjSJvWnmeI09eHZ7xMnmXa1TGVIRprlyTN7pcBxky
# nTuLQwSITQbo+CV5ss/8lN7NZUGAXm0z1HrKTO5w7tvhV4nNk7ipS93ONzBE2WrL
# M/tq4L3Rswg7B8bETDDebvJJXGn7fuVBL6dj+02BVh0r0BGxYK3ZX6LJluPtvlp/
# UADrKd17hw0iJ4WoOpYc2IYj0mlYarKKTsNjAU3LNW0jd+aTy6HjjyRJOqpEeoGO
# hxlFONFY+EjIrhcZrhoEn0DM6zUxgj6uUActRwIDAQABAoIBAEuaT5f5flBvo9ww
# RpAAQXF1wBck0A+u7e9RF1s1wsukBv5/IUVabAuA/myfu94ooym4UPfKzexpMyn1
# sSJdmFzmvb5paj+J4KexqI9wHi0sKDayHDH15keLFs3A2Rk8ilALJRfRd1tdVWHf
# 8cziBvPD1cnSgloyI/WGCl7fpds7yzbFXVtgXCVHixH/9SOB+lafXUhyJksJRJpQ
# WP4yDau5K3nem4REl2GvQ1TuAm2HBQ9dweYHjlDSPN1WRtfNgKuZ1zeRQ89+JY90
# yZXFklPioVpGuw6Ax4Jghrq87a3BvjRES5N6e/tHgb+KpkoaKBan+4/dN1iJCqi0
# d+tcBVECgYEA060PBHBZZ0dgcLIvB5W938mi4YqhT81kKqk5ZTe/SE0ZAiVnZxe1
# +pTYG9vGZkB4CwCEaDob2ukK3Hxya8O4YR2qgJdAVk8cSGqj33mwO37/RKD6VIT1
# EYes8sL/t4kEHqtxDvxU78SzYyJdGGb0pnGvKGxflKx7153HjrXVp60CgYEA/GRQ
# WHNOQphErtvEUEipJRzbR0Wq5MHQOvCTC5QR/TYZgYITEOD8YNWj3uVXrteaSZ/w
# K54rwBdpYvyuuRWq5deau3HPhkvsEpeikk6Eb162wiIQ42Eko8PnCmy+BbUE+Flx
# U9T41EfkdN1bObRbd2OqTXBlktfKEqTWAN+y10MCgYAf6uZqyu4QLqkSFSwWPrQE
# vIi87YRpXhUOgbnP01oactWkhzNSTjb4c90qRjdiT7JKJmfQt4JfvegPWwx9x2NT
# 8X82KJhg60jeeoX/OoAiWIHxPTzB5dJ2NDkV2eVpLVXbsgo4MkA0bzqFZjcXaN7X
# AilhNQYsit2Zo4bls/FleQKBgDeeO35iWnqeZ3RJBafTe0Ksaz33gkNK2oJChYTl
# qlksVM6PRXhQvAzyx1vVGk9zP5K95gUWo/l+r0CbAj3TIofnzTdFS0AC9xDZzX+E
# Qfbw3kFFlIcm3xYfk4hekjlbvK6lty2MHxFYjmWaagH7VrSmh97sx9VmLCeTn30t
# zpFVAoGBALC1esa69Xhm0RzEnGh14hf3v7Pf7iznx9LyplBKpp0U6zQHa71abbVd
# opqfBWNGdGI26Mhs3I0i7nqyPTpm43vkoDL9cxjYGUO30V+lXJ/mPYxgyCAk7JNi
# afPqWUw6nOqI+vb/S/lmMImqhZ0KW7lD2uL725vabUHRGjtlzdLX
# -----END RSA PRIVATE KEY-----




import requests

url = "https://external-api.kalshi.com/trade-api/v2/historical/markets?limit=100&series_ticker=KXBTC15M"

response = requests.get(url)

print(response.text)