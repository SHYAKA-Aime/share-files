import time
from parser import parse_transactions

def linear_search(transactions, transaction_id):
    """
    Linear search: O(n) time complexity
    Scans through the list sequentially until match is found
    """
    for transaction in transactions:
        if transaction.get('id') == transaction_id:
            return transaction
    return None

def dictionary_lookup(transactions_dict, transaction_id):
    """
    Dictionary lookup: O(1) average time complexity
    Direct key access using hash table
    """
    return transactions_dict.get(transaction_id, None)

def build_transaction_dict(transactions):
    """
    Convert list of transactions to dictionary with id as key
    """
    return {t['id']: t for t in transactions}

def measure_search_time(search_func, *args):
    """
    Measure execution time of a search function
    """
    start_time = time.perf_counter()
    result = search_func(*args)
    end_time = time.perf_counter()
    elapsed_time = (end_time - start_time) * 1000000
    return result, elapsed_time

def compare_search_methods(transactions, num_searches=20):
    """
    Compare linear search vs dictionary lookup performance
    """
    print(f"\n{'='*70}")
    print(f"DSA COMPARISON: Linear Search vs Dictionary Lookup")
    print(f"{'='*70}")
    print(f"Total transactions loaded: {len(transactions)}")
    print(f"Number of searches to perform: {num_searches}\n")
    
    transactions_dict = build_transaction_dict(transactions)
    
    search_ids = list(range(1, min(num_searches + 1, len(transactions) + 1)))
    
    linear_times = []
    dict_times = []
    
    print(f"{'ID':<6} {'Linear Search (μs)':<20} {'Dict Lookup (μs)':<20} {'Speedup':<10}")
    print(f"{'-'*70}")
    
    for search_id in search_ids:
        result_linear, time_linear = measure_search_time(linear_search, transactions, search_id)
        result_dict, time_dict = measure_search_time(dictionary_lookup, transactions_dict, search_id)
        
        linear_times.append(time_linear)
        dict_times.append(time_dict)
        
        speedup = time_linear / time_dict if time_dict > 0 else float('inf')
        
        print(f"{search_id:<6} {time_linear:<20.6f} {time_dict:<20.6f} {speedup:<10.2f}x")
    
    avg_linear = sum(linear_times) / len(linear_times)
    avg_dict = sum(dict_times) / len(dict_times)
    avg_speedup = avg_linear / avg_dict if avg_dict > 0 else float('inf')
    
    print(f"{'-'*70}")
    print(f"{'AVG':<6} {avg_linear:<20.6f} {avg_dict:<20.6f} {avg_speedup:<10.2f}x")
    print(f"\n{'='*70}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"Linear Search Average Time: {avg_linear:.6f} microseconds")
    print(f"Dictionary Lookup Average Time: {avg_dict:.6f} microseconds")
    print(f"Performance Improvement: {avg_speedup:.2f}x faster with dictionary")
    print(f"\nTime Complexity:")
    print(f"  - Linear Search: O(n) - must scan through all elements")
    print(f"  - Dictionary Lookup: O(1) - direct hash table access")
    print(f"\nWhy Dictionary is Faster:")
    print(f"  - Uses hash table for constant-time key lookup")
    print(f"  - No sequential scanning required")
    print(f"  - Scales better with larger datasets")
    print(f"\nAlternative Data Structures:")
    print(f"  - Binary Search Tree: O(log n) search time")
    print(f"  - Hash Set: O(1) membership testing")
    print(f"  - Trie: Efficient for prefix-based searches")
    print(f"{'='*70}\n")
    
    return {
        'linear_avg': avg_linear,
        'dict_avg': avg_dict,
        'speedup': avg_speedup,
        'linear_times': linear_times,
        'dict_times': dict_times
    }

if __name__ == '__main__':
    try:
        print("Loading transactions from XML...")
        transactions = parse_transactions("modified_sms_v2.xml")
        print(f"Successfully loaded {len(transactions)} transactions")
        
        results = compare_search_methods(transactions, num_searches=20)
        
    except FileNotFoundError:
        print("Error: modified_sms_v2.xml not found")
    except Exception as e:
        print(f"Error: {e}")
