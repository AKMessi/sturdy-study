import chromadb

# 1. Connect to our persistent database
client = chromadb.PersistentClient(path="chroma_db")

# 2. Get a list of all collections
collections = client.list_collections()

print("\n--- 📚 Your 'user_id' Collections (with doc counts) ---")

if not collections:
    print("No collections found. You may need to upload a document first.")
else:
    for c in collections:
        # 3. Get the count of items in the collection
        count = c.count()
        
        # 4. Print the name and the count
        print(f"  - {c.name}: {count} documents")
        
print("-----------------------------------------------------------\n")