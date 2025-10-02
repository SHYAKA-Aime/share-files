import time
import json

def linear_search(transactions, target_id):
    """Linear search through list to find transaction by ID"""
    for transaction in transactions:
        if transaction['id'] == target_id:
            return transaction
    return None

def dictionary_lookup(transaction_dict, target_id):
    """Dictionary lookup using key-based access"""
    return transaction_dict.get(target_id)

def create_transaction_dict(transactions):
    """Convert list of transactions to dictionary with id as key"""
    return {t['id']: t for t in transactions}

def benchmark_search(transactions, search_ids):
    """Compare performance of linear search vs dictionary lookup"""
    transaction_dict = create_transaction_dict(transactions)
    
    results = {
        'linear_search': {'times': [], 'avg_time': 0},
        'dict_lookup': {'times': [], 'avg_time': 0}
    }
    
    # Benchmark linear search
    for target_id in search_ids:
        start = time.perf_counter()
        result = linear_search(transactions, target_id)
        end = time.perf_counter()
        results['linear_search']['times'].append(end - start)
    
    # Benchmark dictionary lookup
    for target_id in search_ids:
        start = time.perf_counter()
        result = dictionary_lookup(transaction_dict, target_id)
        end = time.perf_counter()
        results['dict_lookup']['times'].append(end - start)
    
    # Calculate averages
    results['linear_search']['avg_time'] = sum(results['linear_search']['times']) / len(results['linear_search']['times'])
    results['dict_lookup']['avg_time'] = sum(results['dict_lookup']['times']) / len(results['dict_lookup']['times'])
    
    return results

def print_benchmark_results(results):
    """Print formatted benchmark results"""
    print("\n" + "="*60)
    print("SEARCH ALGORITHM PERFORMANCE COMPARISON")
    print("="*60)
    
    print(f"\nLinear Search Average Time: {results['linear_search']['avg_time']:.10f} seconds")
    print(f"Dictionary Lookup Average Time: {results['dict_lookup']['avg_time']:.10f} seconds")
    
    speedup = results['linear_search']['avg_time'] / results['dict_lookup']['avg_time']
    print(f"\nSpeedup Factor: {speedup:.2f}x faster with dictionary lookup")
    
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("="*60)
    print("Dictionary lookup is faster because:")
    print("- Time Complexity: O(1) average vs O(n) for linear search")
    print("- Direct key-based access using hash tables")
    print("- No need to iterate through entire list")
    print("\Other Data Structures:")
    print("- Binary Search Tree (BST): O(log n) search time")
    print("- Hash Table with chaining: O(1) average case")
    print("- Trie: Efficient for string-based keys")
    print("="*60 + "\n")

if __name__ == '__main__':
    # Load transactions
    with open('data/processed/transactions.json', 'r') as f:
        transactions = json.load(f)
    
    # Test with at least 20 searches
    search_ids = list(range(1, min(21, len(transactions) + 1)))
    
    print(f"Running benchmark with {len(search_ids)} searches on {len(transactions)} transactions...")
    
    results = benchmark_search(transactions, search_ids)
    print_benchmark_results(results)
