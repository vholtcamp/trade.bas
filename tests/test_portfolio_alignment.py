from trade_objects import format_company_row, format_summary_row, money_decimal_column


def test_summary_decimal_aligns_with_plain_company_row():
    company_row = format_company_row("A:", 37, "$1,750.00")
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row("Stocks:", "$105,250.00", decimal_anchor)

    assert money_decimal_column(summary_row) == decimal_anchor


def test_summary_decimal_aligns_with_ansi_colored_company_row():
    colored_label = "\x1b[31mA\x1b[0m:"
    company_row = format_company_row(colored_label, 62, "$300.00")
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row("Total:", "$351,308.00", decimal_anchor)

    assert money_decimal_column(summary_row) == decimal_anchor


def test_summary_decimal_aligns_with_non_csi_terminal_escapes():
    # Some terminals emit ESC(B alongside CSI color/reset sequences.
    colored_label = "\x1b(B\x1b[31mA\x1b(B\x1b[m:"
    company_row = format_company_row(colored_label, 35, "$2,500.00")
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row("Stocks:", "$143,100.00", decimal_anchor)

    assert money_decimal_column(summary_row) == decimal_anchor
