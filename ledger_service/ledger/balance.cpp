#include <iostream>

using namespace std;

double get_balance(double debit_sum, double credit_sum){
    auto balance = debit_sum - credit_sum;
    return balance;
}

double project_balance(double current, double debit, double credit) {
    //Used to calculate “new balance” without writing to DB yet (e.g. during a payment preview).
    if (debit){
        return current + debit;
    }

    if (credit){
        return current + credit;
    }

    return current;
}

double trial_balance(double credit_sum, double debit_sum) {
    return debit_sum - credit_sum       //should always be equal to 0
}