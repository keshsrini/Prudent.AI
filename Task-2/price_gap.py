def find_price_gap_pair(nums: list[int], k: int) -> tuple[int, int] | None:
    map={}
    small=None
    
    for i,num in enumerate(nums):
        for target in [num-k,num+k]:
            if target in map:
                j=map[target]
                pair=(j,i)
                if small is None or pair<small:
                    small=pair
        if num not in map:
            map[num]=i
            
    return small