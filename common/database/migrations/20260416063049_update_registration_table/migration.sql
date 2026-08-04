/*
  Warnings:

  - You are about to drop the column `capability_id` on the `auth_strategies` table. All the data in the column will be lost.

*/
-- DropForeignKey
ALTER TABLE "auth_strategies" DROP CONSTRAINT "auth_strategies_capability_id_fkey";

-- DropIndex
DROP INDEX "auth_strategies_capability_id_idx";

-- AlterTable
ALTER TABLE "auth_strategies" DROP COLUMN "capability_id",
ADD COLUMN     "capability_ids" TEXT[] DEFAULT ARRAY[]::TEXT[];
