from outline.client import OutlineClient

client = OutlineClient(base_url="https://localhost:777/secretpath")

new_key = client.new(name="New key!")

# set a data limit of 1GB
new_key.change_data_limit(1000000000)

new_key.url("my key with 1GB limit")
# ss://example@example.com/?outline=1#my key with 1GB limit
