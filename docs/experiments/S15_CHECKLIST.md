# S15 — Lab checklist

- [ ] ≥2 voluntary devices  
- [ ] TLS only (no plaintext)  
- [ ] Experiment ID recorded  
- [ ] TextWorld / self-check allowlisted jobs only  
- [ ] Events quarantined  
- [ ] Kill switch verified per device  
- [ ] Fault battery green  
- [ ] No federated learning enabled  
- [ ] Core fortress green  

Commands:

```bash
nexo-lab tls-policy
nexo-lab rehearse --root data/nexo_lab --seed 15
python -m pytest tests/test_s15_multi_device_lab.py tests/test_swarm_core_fortress.py -q
```
