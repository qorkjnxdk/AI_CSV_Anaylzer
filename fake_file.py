with open("fake.csv", "wb") as f:
    f.write(b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 200)