# DR-Altimeter
**Altitude '[Dead Reckoning](https://en.wikipedia.org/wiki/Dead_reckoning)' for Casio Triple Sensor v.3**

_DR-Altimeter_ predicts how much the indicated altitude will deviate due to changing weather in the vicinity of a [Wunderground.com](http://wunderground.com) station. By substracting the predicted altitude change, to remove its influence, one can greatly improve the accuracy of the _Casio Pro Trek_ wristwatch altimeter. Depending on the accuracy of the weather forecast, the indicated altitude can follow true altitude well within a ± 5 meters error margin.

#### Some features

- Fully configurable with an .ini file
- Predictions both produced in graphical and text format;
- Text results can be automatically posted to a [Slack](https://slack.com) chat room, therefore to a smartphone;
- Graphical User Interface (GUI) with zoom and pan functions, to export portions of the graph that interests you specifically
- Command line options, useful notably to create shortcuts and scheduled tasks (Windows equivalent of a cron job)


##### Figure 1: Graphical output
![graphical output](example/graph_example.png)

#### Measuring altitudes based on changes in atmospheric pressure
The altimeter determines the altitude at your current location based on accumulated atmospheric pressure changes measured by the pressure sensor. Setting the altimeter at a location where you know the precise altitude before starting your ascent enables it to take even more precise altitude measurements.

#### Sea level measurement
Setting the altimeter at a location where you know the precise altitude enables you to determine the elevation of your current position with respect to sea level. If you come across a marker indicating 400 meters above sea level while hiking or climbing, for example, simply set the altimeter at 400 meters. This enables you to obtain more accurate readings with respect to sea

#### Vertical Dead Reckoning
[_Dead Reckoning_](https://en.wikipedia.org/wiki/Dead_reckoning) is the process of calculating one's current position by using a previously determined position, or fix, and advancing that position based upon known or estimated speeds over elapsed time and course. 

_Altitude dead reckoning_ uses the same principle as dead reckoning but applies it to the vertical plane. Whilst standing still at a fixed altitude, you'll notice that the altimeter perceives atmospheric pressure variations due to weather changes as altitude changes _as if you climbed or descended_. DR Altimeter displays in brackets [] the expected contribution of weather changes to the indicated altitude.

## Example of use

##### Figure 2: Text output
```
  H      PRESSURE       ALT     ALT/hr                                         
===============================================================================
21h00   1018.63 hPa                      21h01[fix], 21h12[1], 21h47[2]        
-------------------------------------------------------------------------------
 22h    1018.59 hPa      0.3m     0.3m   22h04[1]                              
-------------------------------------------------------------------------------
 23h    1018.39 hPa      2.0m     1.7m                                         
-------------------------------------------------------------------------------
 0h     1018.39 hPa      2.0m     0.0m   00h02[2], 00h44[3]                    
-------------------------------------------------------------------------------
 1h     1018.29 hPa      2.8m     0.8m   01h16[4], 01h49[5]                    
-------------------------------------------------------------------------------
 2h     1018.09 hPa      4.5m     1.7m   02h28[6]                              
-------------------------------------------------------------------------------
 3h     1017.98 hPa      5.4m     0.9m                                         
-------------------------------------------------------------------------------
 4h     1017.90 hPa      6.1m     0.7m   04h48[5]                              
-------------------------------------------------------------------------------
 5h     1017.98 hPa      5.4m    -0.7m   05h31[4]                              
-------------------------------------------------------------------------------
 6h     1018.09 hPa      4.5m    -0.9m   06h09[3], 06h49[2]                    
-------------------------------------------------------------------------------
 7h     1018.23 hPa      3.3m    -1.2m                                         
-------------------------------------------------------------------------------
 8h     1018.51 hPa      1.0m    -2.3m                                         
-------------------------------------------------------------------------------
 9h     1018.53 hPa      0.8m    -0.2m   09h24[3], 09h55[4]                    
-------------------------------------------------------------------------------
 10h    1018.21 hPa      3.5m     2.7m   10h19[5], 10h40[6], 10h59[7]          
-------------------------------------------------------------------------------
 11h    1017.81 hPa      6.8m     3.3m   11h17[8], 11h34[9], 11h51[10]         
-------------------------------------------------------------------------------
 12h    1017.38 hPa     10.4m     3.6m   12h07[11], 12h24[12], 12h40[13],      
                                         12h57[14]                             
-------------------------------------------------------------------------------
 13h    1017.00 hPa     13.5m     3.2m   13h15[15], 13h34[16], 13h55[17]       
-------------------------------------------------------------------------------
 14h    1016.58 hPa     17.0m     3.5m   14h20[18], 14h50[19]                  
-------------------------------------------------------------------------------
 15h    1016.28 hPa     19.5m     2.5m   15h38[20]                             
-------------------------------------------------------------------------------
 16h    1016.28 hPa     19.5m     0.0m                                         
-------------------------------------------------------------------------------
 17h    1016.31 hPa     19.3m    -0.2m   17h29[19]                             
-------------------------------------------------------------------------------
 18h    1016.40 hPa     18.5m    -0.7m                                         
-------------------------------------------------------------------------------
 19h    1016.31 hPa     19.3m     0.7m   19h32[20]                             
-------------------------------------------------------------------------------
 20h    1016.08 hPa     21.2m     1.9m   20h13[21], 20h38[22], 20h58[23]       
-------------------------------------------------------------------------------
 21h    1015.91 hPa     22.6m     1.4m   21h16[24], 21h32[25], 21h46[26]       
-------------------------------------------------------------------------------
 22h    1015.51 hPa     25.9m     3.3m   22h01[27], 22h14[28], 22h28[29],      
                                         22h43[30], 22h58[31]                  
-------------------------------------------------------------------------------
 23h    1014.91 hPa     30.9m     5.0m   23h15[32], 23h38[33]                  
````

##### Simple Example
At 21h01, you determine that you are at an known altitude of 450 meters above mean sea level. This is your reference or initial [fix].

      21h01[fix] @ [0] = 450m ASL

Later, at twelve minutes passed midnight, your watch indicates an altitude of 476 meters. And since, between 00h02 and 00h43, the expected contribution of weather is 2 meters (see [Figure 2](README.md#figure-2-textual-output)), you can estimate your true altitude to be 476 - 2 = 474 meter above sea level.

      00h12[I] = 476m, indicated
      00h12[DR] = 476m - 00h02[2] = 474m ASL, compensated for forecasted weather
      
##### More Advanced Example
On the same trek ([see above](DR-Altimeter#simple-use)), at 00h50, you reach a point of known altitude (523m ASL). You recalibrate your watch to match this know altitude. Here and on after, this new [fix] becomes your new reference.

      00h50[fix] @ [3] = 523m ASL
     
Next morning, at 07:30, your watch indicates an altitude of 478m. Since your last fix was taken at the [3] compensation level (00h44[3]) and you are current at the [2] compensation level (06h49[2]), your deduced altitude is 478 + @[3] - [2] = 479 m.

      07h30[I] = 478m, indicated
      07h30[DR] = (478m + @ 0044[3]) - 06h49[2]
                = 481 - 2
                = 479m ASL, compensated for forecasted weather 
               
## Installation

See [INSTALL.md](INSTALL.md)

##  Configuration

See [CONFIG.md](CONFIG.md)

## Command Line Options

See [COMMAND.md](COMMAND.md)

## Known Issues

- **[Top right y axis (altitude) : scale not formatted](https://github.com/Wlodarski/DR-Altimeter/issues/1)**  
  - A [temporary solution](https://github.com/matplotlib/matplotlib/issues/15621#issuecomment-571744504) is to manually edit axis.py, line 760. 
  - The definitive solution is to wait for the [matplotlib](https://matplotlib.org/) library to updated. The patch to squash that bug is scheduled to be included with version 0.3.30. Please execute `pip install --upgrade matplotlib` when it will available.
