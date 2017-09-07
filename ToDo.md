# General:
- [x] add Tournament(players=[...]) to evaluate relative strength 
- [ ] add optional opening randomization for all (esp. deterministic) players

# Optimization:
Current performance is ~0.3s/game - evaluation/training would be faster if this could be improved
- profile and optimize performance if possible
- think about a more efficient eval of legal moves

# Players
- [x] add Human player
- [ ] add randomization between equal options for all value-based players
- [ ] generalize value-based players

- add minimax/alpha-beta-pruning player
- add player with genetically evolving weights?
- add/train NN player
