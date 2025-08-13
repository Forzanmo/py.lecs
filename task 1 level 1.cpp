#include <iostream>
using namespace std;
#include <string>

bool isnum(const string n) { 
    bool x = 0;
    for (char ch : n) { 
        if (47 < ch && ch < 58) { // check ASCII for '0'-'9'
            x = 1;
        }
        else {
            x = 0;
            break; // stop at first non-digit
        }
    }
    return x;
}

int main() {
    string s1, s2;//to check then make it n1 ad n2
    float n1, n2;
    int x;

    cout << "Hello to our simple Calculator" << endl
         << "Please make sure to enter numbers only to avoid errors." << endl;

    cout << "Enter first number: ";
    cin >> s1;
    if (!isnum(s1)) {
        cout << "Error: invalid number!" << endl;
        return 1; // terminate program
    }
    n1 = stof(s1);//casting

    cout << "Enter second number: ";
    cin >> s2;
    if (!isnum(s2)) {
        cout << "Error: invalid number!" << endl;
        return 1;
    }
    n2 = stof(s2);

    cout << "Select operation:" << endl
         << "1 - Addition" << endl
         << "2 - Subtraction" << endl
         << "3 - Multiplication" << endl
         << "4 - Division" << endl;

    cin >> x;

    switch (x) {
        case 1:
            cout << n1 << " + " << n2 << " = " << n1 + n2 << endl;
            break;
        case 2:
            cout << n1 << " - " << n2 << " = " << n1 - n2 << endl;
            break;
        case 3:
            cout << n1 << " * " << n2 << " = " << n1 * n2 << endl;
            break;
        case 4:
            if (n2 == 0) {
                cout << "Error  division by zero" << endl;
            } else {
                cout << n1 << " / " << n2 << " = " << n1 / n2 << endl;
            }
            break;
        default:
            cout << "Invalid operation!" << endl;
    }

    return 0;
}
