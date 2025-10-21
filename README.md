The repo contains three QuantConnect Algorithm each demonstrating different features and functionalities.    
### 1. Future Rollover Algorithm
Future Positions rollover which happens 5 days prior to expiry of current contract. I have considered Quarterly expiry contracts.    
### 2. Position Management
Adds Positions in the same direction after encountering a winning position, the additions are based on pyramiding -     

Each successive addition follows a geometric scaling:  

$$
P_n = P_0 \cdot r^{(n - 1)}
$$     

where Pn is the size of the nth addition, P0 is the initial position, and r is the scaling ratio set as 0.5.            
The average entry price is calculated as below-    

$$
\text{Average Price} = \frac{\displaystyle\sum_{i=1}^{n} (P_i \times Q_i)}{\displaystyle\sum_{i=1}^{n} Q_i}
$$    

The *Stop Loss* is adjusted based on the maximum risk of equity which is 8%.    
### 3. Connecting to QuantConnect using RESTAPI Interface
This snippet contains the code to connect to the quantconnect project and edit parameters and run different available 
features.       


