from inf349.redis_client import redis_client

redis_client.set("test_key", "hello Redis!")
print(redis_client.get("test_key"))  # Doit afficher : hello Redis!
