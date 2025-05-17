import time
from multiprocessing import Pool, cpu_count

def factorize_number(n):
    factors = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            factors.append(i)
            if i != n // i:
                factors.append(n // i)
    return sorted(factors)

def factorize_sync(*numbers):
    return [factorize_number(n) for n in numbers]

def factorize_parallel(*numbers):
    with Pool(cpu_count()) as pool:
        results = pool.map(factorize_number, numbers)
    return results

def main():
    nums = (128, 255, 99999, 10651060)

    start = time.perf_counter()
    sync_results = factorize_sync(*nums)
    end = time.perf_counter()
    print(f"Sync time: {end - start:.4f} seconds")

    start = time.perf_counter()
    parallel_results = factorize_parallel(*nums)
    end = time.perf_counter()
    print(f"Parallel time: {end - start:.4f} seconds")

    # Перевірка правильності
    a, b, c, d = parallel_results
    assert a == [1, 2, 4, 8, 16, 32, 64, 128]
    assert b == [1, 3, 5, 15, 17, 51, 85, 255]
    assert c == [1, 3, 9, 41, 123, 271, 369, 813, 2439, 11111, 33333, 99999]
    assert d == [1, 2, 4, 5, 7, 10, 14, 20, 28, 35, 70, 140, 76079, 152158, 304316,
                 380395, 532553, 760790, 1065106, 1521580, 2130212, 2662765, 5325530, 10651060]
    print("All assertions passed.")

if __name__ == "__main__":
    main()
