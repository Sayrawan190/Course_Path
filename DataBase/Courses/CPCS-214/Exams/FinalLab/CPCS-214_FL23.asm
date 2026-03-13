.data
menu:   .asciiz "Menu:\n1. Add Patient ID\n2. Display Patients\n3. Search Patient ID\n4. Exit\n"
prompt: .asciiz "Enter your choice: "
invalid: .asciiz "Invalid choice. Please try again.\n"
patient: .word 123456, 123457, 123458, 0, 0, 0
space: .asciiz " "
search: .asciiz "Enter ID to Search: "
found: .asciiz "ID found\n"
notfound: .asciiz "ID NOT found\n"
newline: .asciiz "\n"

.text
.globl main

main:
    li $v0, 4
    la $a0, menu
    syscall

    li $v0, 4
    la $a0, prompt
    syscall

    li $v0, 5
    syscall
    move $t0, $v0

    beq $t0, 1, AddPatient
    beq $t0, 2, PrintPatients
    beq $t0, 3, SearchPatient
    beq $t0, 4, exit
    j invalid_choice


    AddPatient:
    la $t2, patient

    FindEmpty:
    lw $t3, 0($t2)
    beq $t3, $zero, Done
    addi $t2, $t2, 4
    j FindEmpty

    Done:
    li $t1, 112233
    sw $t1, 0($t2)

    j main


    PrintPatients:
    la $t2, patient

    pri_loop:
    lw $t4, 0($t2)
    beq $t4, $zero, end_pri

    move $a0, $t4
    li $v0, 1
    syscall

    li $v0, 4
    la $a0, space
    syscall

    addi $t2, $t2, 4
    j pri_loop

    end_pri:
    li $v0, 4
    la $a0, newline
    syscall
    j main


    SearchPatient:
    li $v0, 4
    la $a0, search
    syscall

    li $v0, 5
    syscall
    move $t0, $v0 

    la $t1, patient

    se_loop:
    lw $t2, 0($t1)
    beq $t2, $zero, not_found
    beq $t2, $t0, found_id

    addi $t1, $t1, 4
    j se_loop

    found_id:
    li $v0, 4
    la $a0, found
    syscall
    j main

    not_found:
    li $v0, 4
    la $a0, notfound
    syscall
    j main


    invalid_choice:
    li $v0, 4
    la $a0, invalid
    syscall
    j main


    exit:
    li $v0, 10
    syscall