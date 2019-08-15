import re
import operator
import argparse

ClassToAnalysisDetailsHolder = {}
ClassToChangedSizeCountMap = {}

# Column Number in Histogram file
# slNumCol=0
numOfInstancesCol = 1
sizeOfInstancesCol = 2
classNameCol = 3

secondClassNameToHistosMap = {}
firstClassNameToHistosMap = {}
nokiaPackageFilters = ['com\.nokia.*']
javaPackages = ['^\[.*', '^java.*']
OutputTable = []


class AnalysisDetails:
    def __init__(self):
        self.className = None
        self.instance_count_variance = None
        self.instance_size_variance = None
        self.count_variance_percentage = None
        self.size_variance_percentage = None

    def get_class_name(self):
        return self.className

    def set_class_name(self, class_name):
        self.className = class_name

    def get_inst_count_variance(self):
        return self.instance_count_variance

    def set_inst_count_variance(self, instance_count_variance):
        self.instance_count_variance = instance_count_variance

    def get_count_variance_per(self):
        return self.count_variance_percentage

    def set_count_variance_per(self, count_variance_percentage):
        self.count_variance_percentage = count_variance_percentage

    def get_size_vari_per(self):
        return self.size_variance_percentage

    def set_size_vari_per(self, size_variance_percentage):
        self.size_variance_percentage = size_variance_percentage

    def get_inst_size_vari(self):
        return self.instance_size_variance

    def set_inst_size_vari(self, instance_size_variance):
        self.instance_size_variance = instance_size_variance


class Histogram:
    def __init__(self):
        self.instance_count = 0
        self.instance_size = 0

    def get_instance_count(self):
        return self.instance_count

    def set_instance_count(self, instance_count):
        self.instance_count = instance_count

    def get_instance_size(self):
        return self.instance_size

    def set_instance_size(self, instance_size):
        self.instance_size = instance_size


def load_record_to_map(line, map):
    if ':' in line:
        spliced_line = line.split()
        if len(spliced_line) > 1:
            histogram = Histogram()
            histogram.set_instance_count(spliced_line[numOfInstancesCol])
            histogram.set_instance_size(spliced_line[sizeOfInstancesCol])
            map[spliced_line[classNameCol]] = histogram


def parse_files(firstRunGCHistoFile, secondRunGCHistoFile):
    with open(secondRunGCHistoFile) as s_File:
        line = s_File.readline()
        while line:
            line.strip()
            line = s_File.readline()
            load_record_to_map(line, secondClassNameToHistosMap)

    with open(firstRunGCHistoFile) as f_File:
        line = f_File.readline()
        while line:
            line.strip()
            line = f_File.readline()
            load_record_to_map(line, firstClassNameToHistosMap)


def sort_desc_order_by_count_percentage(map):
    return sorted(map.values(), key=operator.attrgetter('count_variance_percentage'), reverse=True)


def sort_desc_order_by_size_percentage(map):
    return sorted(map.values(), key=operator.attrgetter('size_variance_percentage'), reverse=True)


def get_size_diff(second_histogram, first_histogram):
    return int(second_histogram.get_instance_size()) - int(first_histogram.get_instance_size())


def get_instance_diff(second_histogram, first_histogram):
    return int(second_histogram.get_instance_count()) - int(
        first_histogram.get_instance_count())


def get_variance(increase, oldValue):
    # To calculate the percentage increase:
    # Increase = New Number - Original Number
    # % increase = Increase ÷ Original Number × 100.
    # If your answer is a negative number then this is a percentage decrease.
    percentage_increase = (increase / int(oldValue)) * 100
    return round(percentage_increase, 2)


def bytes_to_KB(sizeincrease):
    return sizeincrease / 1024


def get_analysis_details(className, second_histogram, first_histogram):
    analysis_details = AnalysisDetails()

    analysis_details.set_class_name(className)

    increased_inst_count = get_instance_diff(second_histogram, first_histogram)
    analysis_details.set_inst_count_variance(increased_inst_count)
    analysis_details.set_count_variance_per(
        get_variance(increased_inst_count, first_histogram.get_instance_count()))

    increased_inst_size = get_size_diff(second_histogram, first_histogram)
    analysis_details.set_inst_size_vari(round(bytes_to_KB(increased_inst_size)))
    analysis_details.set_size_vari_per(
        get_variance(increased_inst_size, first_histogram.get_instance_size()))
    return analysis_details


def process():
    for className in firstClassNameToHistosMap:
        first_histogram = firstClassNameToHistosMap[className]
        second_histogram = secondClassNameToHistosMap[className]

        if second_histogram:
            ClassToAnalysisDetailsHolder[className] = get_analysis_details(className, second_histogram,
                                                                           first_histogram)


def is3rdPartyPackage(analysisDetails):
    ignoreList = nokiaPackageFilters + javaPackages
    is3rdParty = False
    if len(ignoreList) > 0:
        for pkg_regex in ignoreList:
            isIgnorePkg = re.match(pkg_regex, analysisDetails.get_class_name(), re.IGNORECASE)
            if isIgnorePkg:
                break
        if isIgnorePkg:
            pass
        else:
            is3rdParty = True
    return is3rdParty


def isNokiaPackage(analysisDetails):
    if len(nokiaPackageFilters) > 0:
        for pkg_regex in nokiaPackageFilters:
            isIgnorePkg = re.match(pkg_regex, analysisDetails.get_class_name(), re.IGNORECASE)
            if isIgnorePkg:
                return True


def printDotLine():
    OutputTable.append(
        ['-----------------------------------------------------------------', '-----------------------------',
         '-------------------------------'])


def printSizeVarienceLine(analysisDetails):
    OutputTable.append([analysisDetails.get_class_name(), str(analysisDetails.get_inst_size_vari()),
                        str(analysisDetails.get_size_vari_per())])


def printCountVarianceLine(analysisDetails):
    OutputTable.append([analysisDetails.get_class_name(), str(analysisDetails.get_inst_count_variance()),
                        str(analysisDetails.get_count_variance_per())])


def printCountHeader():
    OutputTable.append(
        ['--Top ' + str(args.top) + ' ' + args.reportType + ' Leak Suspects by Instance count Report--', '', ''])
    printDotLine()
    OutputTable.append(['Object Name', 'Non reclaimed Instances count', 'Variance of instance count in %'])
    printDotLine()


def generateCountVarianceReport():
    count_variance_sorted_ad_map = sort_desc_order_by_count_percentage(ClassToAnalysisDetailsHolder)
    printCountHeader()
    count = 0
    for (analysisDetails) in count_variance_sorted_ad_map:
        if count < args.top:
            if args.reportType == 'nokiaonly':
                if isNokiaPackage(analysisDetails):
                    count += 1
                    printCountVarianceLine(analysisDetails)
            elif args.reportType == '3rdponly':
                if is3rdPartyPackage(analysisDetails):
                    count += 1
                    printCountVarianceLine(analysisDetails)
            else:
                count += 1
                printCountVarianceLine(analysisDetails)
    printDotLine()


def printSizeHeader():
    OutputTable.append(['--Top ' + str(args.top) + ' ' + args.reportType + ' Suspects by Memory Size Report--', '', ''])
    printDotLine()
    OutputTable.append(['Object Name', 'Non reclaimed Memory in KB', 'Variance of Mem Size in %'])
    printDotLine()


def generateSizevarianceReport():
    size_variance_sorted_ad_map = sort_desc_order_by_size_percentage(ClassToAnalysisDetailsHolder)
    printSizeHeader()
    count = 0
    for (analysisDetails) in size_variance_sorted_ad_map:
        if count < args.top:
            if args.reportType == 'nokiaonly':
                if isNokiaPackage(analysisDetails):
                    count += 1
                    printSizeVarienceLine(analysisDetails)
            elif args.reportType == '3rdponly':
                if is3rdPartyPackage(analysisDetails):
                    count += 1
                    printSizeVarienceLine(analysisDetails)
            else:
                count += 1
                printSizeVarienceLine(analysisDetails)
    printDotLine()


def generateReports():
    OutputTable.append(['', '', ''])
    generateCountVarianceReport()

    OutputTable.append(['', '', ''])
    generateSizevarianceReport()


def print_report():
    longest_cols = [
        (max([len(str(row[i])) for row in OutputTable]) + 3)
        for i in range(len(OutputTable[0]))
    ]
    row_format = "".join(["{:>" + str(longest_col) + "}" for longest_col in longest_cols])
    for row in OutputTable:
        print(row_format.format(*row))


def main():
    # print("Reference https://gist.github.com/alexcpn/a68761c94c85f0210413")
    parser = argparse.ArgumentParser(
        description='A Python Script to parse the Jcmd generated Histograms and Report top Suspect Memory Leak objects')
    # Optional arguments
    parser.add_argument('reportType', default='all', const='all', nargs='?', choices=['nokiaonly', '3rdponly', 'all'])
    parser.add_argument('--top', type=int, default=20, help='How Many leak Suspects shown in report')
    # Mandatory arguments
    parser.add_argument('-f', '--finputfile', help='first Histogram file name', required=True)
    parser.add_argument('-s', '--sinputfile', help='second Histogram file name', required=True)

    global args
    args = parser.parse_args()
    print('Arguments passed:' + str(args))
    parse_files(args.finputfile, args.sinputfile)
    process()
    generateReports()
    print_report()


if __name__ == "__main__":
    main()
