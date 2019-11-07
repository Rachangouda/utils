# utils

# MemoryLeakSuspectReport.py

Command line tool to suspect the memory leak in java by analysing JCMD class histogram files.

Script will calculate the difference between two jcmd class histograms and displays top N leak suspects sorted by percentage growth.

Note: originally implemented with java coding standards later partially coverted to python coding formats. please ignore code formating. 

# Using this tool

Java process configuration
1. Add -XX:+UnlockDiagnosticVMOptions JVM option to java process to detect memory leak
2. Run testcase/action 
3. Run forceful GC using JCMD `jcmd <pid> GC.run` 
4. Run `jcmd  <pid> GC.class_histogram -all > firstHistogram.txt`
5. Run test case/ action again
6. Run forceful GC again `jcmd <pid> GC.run` 
7. Run `jcmd <pid> GC.class_histogram -all > secondHistogram.txt'

After collecting the histogram files run the script `MemoryLeakSuspectReport -f firstHistogram.txt -s secondHistogram.txt` to get the suspect report.

Report customizations
1. Top N Suspects report `MemoryLeakSuspectReport -f firstHistogram.txt -s secondHistogram.txt --top 5`
2. Package filtered reports, two filters available 'xcompany only' and '3rd party only' 
    To filter your company specific objects add xcompany package identifier xcompany RegEx list in script
    `MemoryLeakSuspectReport -f firstHistogram.txt -s secondHistogram.txt --top 5 3rdponly` or `MemoryLeakSuspectReport -f firstHistogram.txt -s secondHistogram.txt --top 5 xcompanyonly`
