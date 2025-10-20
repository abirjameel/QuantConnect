The repo contains three QuantConnect Algorithm each demonstrating differrent features and functionalities.    
1. Future Rollover - Manual Future Position rollover which happens 5 days prior to expiry of current contract. Quarterly expiry contracts.    
2. Position Management Mathematically - Adds Positions in the same direction after encountering a winning position, the additions are based on pyramiding -     
Each successive addition follows a geometric scaling:    
Pn=P0⋅r^(n−1)     
where Pn is the size of the nth addition, P0 is the initial position, and r is the scaling ratio set as 0.5.​        
