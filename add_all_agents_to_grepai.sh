cd ~/tymemud
for agent in _agent_work/*; do
  grepai workspace add tymemud "$agent"
done
