###################################################
python-outline - Python wrapper for Outline VPN API
###################################################

**python-outline** is a best python wrapper for `Outline API <https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/shadowbox/server/api.yml>`_.

It is a simple and easy to use wrapper for the Outline API.

**********
How to use
**********

.. code:: python

    from outline.client import OutlineClient

    client = OutlineClient(base_url="https://localhost:777/secretpath")
    
    new_key = client.new()
    
    new_key.rename("This is a new name")
    
    # set a data limit of 1GB
    new_key.change_data_limit(1000000000)
    
    new_key.url("my key with 1GB limit")
    # ss://example@example.com/?outline=1#my key with 1GB limit
