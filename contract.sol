// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vulnerable {
    mapping(address => uint) public balances;
    bool private locked;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint amount) public {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount; // Reentrancy risk
    }

    function unusedVariable() public {
        uint x = 42; // Unused variable
    }

    function BAD_NAMING() public pure returns (uint) { // Non-standard naming
        return 1;
    }
}