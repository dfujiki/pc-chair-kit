from util import iterate_csv
import sys

def main():
    report = sys.argv[1]
    output_csv = sys.argv[2]
    types  = sys.argv[3]

    output_lines = ['paper,assignment,email,conflicttype']
    if types == "susp":
        for r in iterate_csv(report):
            valid, paper, email, reasons, comment = r

            if valid=='x':
                output_lines.append("%s,conflict,%s" %(paper, email))
    else:
        for r in iterate_csv(report):
            valid, paper, email, reasons = r

            if valid=='x':
                output_lines.append("%s,conflict,%s,chair-confirmed" %(paper, email))

    with open(output_csv,'w') as f:
        f.write('\n'.join(output_lines))
        f.write('\n')

if __name__ == '__main__':
    main()
