class UsernameGenerator:
    def generate(self, first_name, last_name, birth_year=None):
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        
        # Pre-calculate common substrings for speed
        first_1, first_2, first_3 = first[0], first[:2], first[:3]
        last_1, last_2, last_3 = last[0], last[:2], last[:3]
        
        usernames = []
        
        # Core combinations (most likely to exist)
        usernames.extend([
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first_1}{last}",
            f"{first}{last_1}",
            f"{first_3}{last}",
            f"{first}{last_3}",
            f"{first_2}{last}",
            f"{first}{last_2}"
        ])
        
        # Quick number variations (only 1-5 for speed)
        for i in range(1, 6):
            usernames.extend([
                f"{first}{last}{i}",
                f"{first}{i}{last}",
                f"{i}{first}{last}"
            ])
        
        # Fast separator variations
        for sep in ['.', '_', '-']:
            usernames.extend([
                f"{first}{sep}{last}",
                f"{first_1}{sep}{last}",
                f"{first}{sep}{last_1}"
            ])
        
        # Reversed combinations
        usernames.extend([
            f"{last}{first}",
            f"{last}.{first}",
            f"{last}_{first}",
            f"{last_1}{first}",
            f"{last}{first_1}"
        ])
        
        # Abbreviated versions
        usernames.extend([
            f"{first_1}{last_1}",
            f"{first_2}{last_2}",
            f"{first_3}{last_3}"
        ])
        
        # Top suffixes only (most common)
        for suffix in ['x', '1', '2', 'official']:
            usernames.extend([
                f"{first}{last}{suffix}",
                f"{first}{suffix}",
                f"{last}{suffix}"
            ])
        
        # Birth year variations (if provided)
        if birth_year:
            year_short = str(birth_year)[-2:]
            usernames.extend([
                f"{first}{last}{year_short}",
                f"{first}{year_short}{last}",
                f"{year_short}{first}{last}"
            ])
        
        # Recent years
        usernames.extend([
            f"{first}{last}2024",
            f"{first}{last}2023",
            f"{first}{last}2022"
        ])
        
        # Fast professional variations
        usernames.extend([
            f"{first}{last}ceo",
            f"{first}{last}founder",
            f"{first}{last}pro",
            f"{first}{last}official"
        ])
        
        # Remove duplicates and return optimized list
        unique_usernames = list(set(usernames))
        return unique_usernames[:50]  # Reduced from 71 for speed
