use ore_common::{MiningSolution, OreError, Result};
use solana_sdk::{
    hash::Hash,
    instruction::Instruction,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    system_instruction,
    transaction::Transaction,
};
use std::str::FromStr;
use tracing::info;

/// Builder for constructing Jito bundles
///
/// A bundle typically contains:
/// 1. Tip payment transaction (to Jito)
/// 2. Mining transaction (claim + stake on chosen block)
pub struct BundleBuilder {
    payer: Pubkey,
    tip_account: Pubkey,
}

impl BundleBuilder {
    pub fn new(payer: Pubkey, tip_account: String) -> Result<Self> {
        let tip_pubkey = Pubkey::from_str(&tip_account)
            .map_err(|e| OreError::InvalidConfig(format!("Invalid tip account: {}", e)))?;

        Ok(Self {
            payer,
            tip_account: tip_pubkey,
        })
    }

    /// Build a mining bundle
    ///
    /// This creates a bundle containing:
    /// 1. Jito tip payment
    /// 2. Mine instruction (submit hash proof)
    /// 3. Stake instruction (bet on chosen block)
    pub fn build_mining_bundle(
        &self,
        solution: &MiningSolution,
        target_block: u8,
        stake_amount: u64,
        tip_amount: u64,
        recent_blockhash: Hash,
        keypair: &Keypair,
    ) -> Result<Vec<Transaction>> {
        let mut transactions = Vec::new();

        // Transaction 1: Jito tip
        let tip_tx = self.build_tip_transaction(tip_amount, recent_blockhash, keypair)?;
        transactions.push(tip_tx);

        // Transaction 2: Mine + Stake
        let mine_stake_tx = self.build_mine_stake_transaction(
            solution,
            target_block,
            stake_amount,
            recent_blockhash,
            keypair,
        )?;
        transactions.push(mine_stake_tx);

        info!(
            "Built bundle: tip={}, stake={}, block={}",
            tip_amount, stake_amount, target_block
        );

        Ok(transactions)
    }

    /// Build tip transaction
    fn build_tip_transaction(
        &self,
        tip_amount: u64,
        recent_blockhash: Hash,
        keypair: &Keypair,
    ) -> Result<Transaction> {
        let tip_instruction = system_instruction::transfer(
            &keypair.pubkey(),
            &self.tip_account,
            tip_amount,
        );

        let mut transaction = Transaction::new_with_payer(
            &[tip_instruction],
            Some(&keypair.pubkey()),
        );

        transaction.sign(&[keypair], recent_blockhash);

        Ok(transaction)
    }

    /// Build mine + stake transaction
    ///
    /// This is a simplified version. In production, you would use the actual
    /// ORE V2 program instructions.
    fn build_mine_stake_transaction(
        &self,
        solution: &MiningSolution,
        target_block: u8,
        stake_amount: u64,
        recent_blockhash: Hash,
        keypair: &Keypair,
    ) -> Result<Transaction> {
        // These would be the actual ORE V2 program IDs and instruction builders
        // For now, we'll create placeholder instructions

        let ore_program_id = Pubkey::from_str("ore1111111111111111111111111111111111111111")
            .unwrap();

        // Mine instruction (submit hash proof)
        let mine_instruction = self.build_mine_instruction(
            &ore_program_id,
            solution,
            &keypair.pubkey(),
        );

        // Stake instruction (bet on grid block)
        let stake_instruction = self.build_stake_instruction(
            &ore_program_id,
            target_block,
            stake_amount,
            &keypair.pubkey(),
        );

        let mut transaction = Transaction::new_with_payer(
            &[mine_instruction, stake_instruction],
            Some(&keypair.pubkey()),
        );

        transaction.sign(&[keypair], recent_blockhash);

        Ok(transaction)
    }

    /// Build mine instruction
    ///
    /// In production, this would use the actual ORE V2 program's IDL
    fn build_mine_instruction(
        &self,
        program_id: &Pubkey,
        solution: &MiningSolution,
        miner: &Pubkey,
    ) -> Instruction {
        // Simplified instruction data
        // Real implementation would use anchor_lang::InstructionData
        let mut data = vec![0u8]; // Mine discriminator
        data.extend_from_slice(&solution.nonce.to_le_bytes());
        data.extend_from_slice(&solution.hash);

        Instruction {
            program_id: *program_id,
            accounts: vec![
                // Account metas for mine instruction
                // This would include: miner, proof, config, etc.
            ],
            data,
        }
    }

    /// Build stake instruction
    ///
    /// In production, this would use the actual ORE V2 program's IDL
    fn build_stake_instruction(
        &self,
        program_id: &Pubkey,
        block_index: u8,
        amount: u64,
        staker: &Pubkey,
    ) -> Instruction {
        // Simplified instruction data
        let mut data = vec![1u8]; // Stake discriminator
        data.push(block_index);
        data.extend_from_slice(&amount.to_le_bytes());

        Instruction {
            program_id: *program_id,
            accounts: vec![
                // Account metas for stake instruction
                // This would include: staker, grid, block, treasury, etc.
            ],
            data,
        }
    }

    /// Build a bundle for the "sniper" strategy
    ///
    /// This is optimized for last-second submission with higher tips
    pub fn build_sniper_bundle(
        &self,
        solution: &MiningSolution,
        target_block: u8,
        stake_amount: u64,
        aggressive_tip: u64,
        recent_blockhash: Hash,
        keypair: &Keypair,
    ) -> Result<Vec<Transaction>> {
        info!("Building SNIPER bundle with aggressive tip: {}", aggressive_tip);

        self.build_mining_bundle(
            solution,
            target_block,
            stake_amount,
            aggressive_tip,
            recent_blockhash,
            keypair,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bundle_builder() {
        let keypair = Keypair::new();
        let builder = BundleBuilder::new(
            keypair.pubkey(),
            "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5".to_string(),
        )
        .unwrap();

        let solution = MiningSolution {
            nonce: 12345,
            hash: [0u8; 32],
            difficulty: 10,
            timestamp: 1000000,
            worker_id: "test".to_string(),
        };

        let bundle = builder
            .build_mining_bundle(
                &solution,
                5,
                500_000_000,
                10_000,
                Hash::default(),
                &keypair,
            )
            .unwrap();

        assert_eq!(bundle.len(), 2); // Tip + Mine/Stake
    }
}
