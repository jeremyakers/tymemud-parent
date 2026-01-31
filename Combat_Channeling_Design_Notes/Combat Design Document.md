This is the updated **Combat System Design Document** for your Wheel of Time MUD. It incorporates the resolutions for the previous design issues (Flat ABS, Split Endurance, Bitmasks, and Targeting Logic) to provide a clear blueprint for the **Cursor** coding tool.

# **WoT MUD: Code Combat System Design Document**

## **1\. System Architecture**

The system is a turn-based engine designed to handle high-granularity tactical combat while allowing for automation.

### **Automation Modes:**

* **Manual**: Full control over form and body part selection.  
* **Semi-Automatic**: Player sets "Aggressiveness" and "Target Region"; AI selects the specific form.  
* **Fully Automatic**: AI handles all targeting and form selection based on optimal damage/defense.

## ---

**2\. Core Player Attributes & Pools**

### **Attributes**

* **Strength (Int)**: Range 70–250. Influences base damage and force.  
* **Agility (Float)**: \~1.0. Primary modifier for hit chance and reaction speed.  
* **Constitution (Float)**: \~1.0. Primary modifier for HP/Blood scaling and wound resistance.

### **Dynamic Pools**

* **Health (HP)**: Current/Max. Represents general structural integrity.  
* **Blood**: Current/Max. Bloodloss leads to consciousness loss and severe stat penalties.  
* **Stamina (Physical Endurance)**: Used for Combat Forms and physical maneuvers.  
* **Willpower (Mental Endurance)**: Used for Weaving (One Power) and mental resilience.

## ---

**3\. Data Structures & Bitmasking**

To handle 80+ body parts efficiently, use **64-bit Bitmasks** grouped by region.

### **Body Part Bitmasks (Examples)**

C

// Region: Head (Mask 1\)  
\#define PART\_SKULL        (1ULL \<\< 0\)  
\#define PART\_NECK         (1ULL \<\< 1\)  
\#define PART\_THROAT       (1ULL \<\< 2\)  
\#define PART\_LEFT\_EYE     (1ULL \<\< 3\)  
\#define PART\_RIGHT\_EYE    (1ULL \<\< 4\)

// Region: Body (Mask 2\)  
\#define PART\_HEART        (1ULL \<\< 0\)  
\#define PART\_LUNG         (1ULL \<\< 1\)  
\#define PART\_RIB\_1        (1ULL \<\< 2\)

### **Combat Form Structure**

C

struct combat\_form {  
    int id;  
    char\* name;  
    int tier;            // 0-3  
    int weapon\_req;      // Enum: Sword, Spear, Unarmed, etc.  
    int damage\_type;     // Slash, Pierce, Crush  
    uint64\_t target\_mask\[4\]; // Bits representing allowed body parts  
    float force\_mod;  
    float speed\_mod;  
    int stamina\_cost;  
    // ... specialized proc pointers for special effects  
};

## ---

**4\. Combat Logic & Formulas**

### **The Predictability Penalty (Form Spamming)**

To prevent players from spamming one "best" form, the defender receives a bonus based on the attacker's recent history.

* **History Buffer**: Store the id of the last 3 forms used.  
* **Penalty**:  
  * Current Form \== Last Form: **\-25% Hit Chance**  
  * Current Form \== 2nd Last Form: **\-10% Hit Chance**

### **Readiness & Reaction**

Readiness is a dynamic multiplier (1.1 to 1.5) that determines the effectiveness of the next move.

* **Recovery**: If a player critically fails (Stumble/Fall), Readiness is set to **0.1**, requiring a "Recover" turn to reset to 1.0.

### **Calculation Phase**

1. **Attacker Value**: (Form Skill \* Stamina Mod \* Blood Mod \* Agi Mod) \* Aggressiveness  
2. **Defender Value**: (Defense Skill \* Readiness \* Agi Mod) \* Predictability Bonus  
3. **Outcome**: Compare values. Highest wins the exchange.

## ---

**5\. Armor & Damage (ABS System)**

Armor uses **Flat Damage Reduction (DR)** with a **Soft Cap**.

* **ABS Calculation**: Final\_Damage \= Raw\_Damage \- Armor\_DR.  
* **The 90% Rule**: Armor cannot reduce a hit's damage by more than 90%. (e.g., A 100 damage hit against 150 DR armor still deals 10 damage).  
* **Damage Types**: Armor has three DR values: DR\_Slash / DR\_Pierce / DR\_Crush.

## ---

**6\. Targeting System (Regional Shorthand)**

To simplify manual play, players target **Regions**. The system then resolves the specific **Body Part**.

* **Command**: slash 'overhead' cormac head  
* **Logic**:  
  1. The code identifies the **Head Region**.  
  2. It filters the form's target\_mask against parts in that region.  
  3. It rolls a weighted random to determine the specific hit (e.g., 70% Face/Cheek, 10% Skull, 10% Neck, 10% Eyes).

## ---

**7\. Wound Severity & Instant Death**

Wounds are categorized by damage dealt relative to the body part's HP.

* **Minor**: 0–19% of part HP.  
* **Substantial**: 20–59%.  
* **Gashed**: 60–99% (Triggers massive bleeding).  
* **Severed/Broken**: 100%+ (Permanent disability or instant death for critical parts).

### **Instant Death Triggers:**

* PART\_SKULL status \== BROKEN  
* PART\_HEART status \== GASHED or SEVERED  
* PART\_THROAT status \== SEVERED

## ---

**8\. Requirements for Cursor Implementation**

When implementing this system, ensure:

1. The injury\_mod is a product of all active wounds (multiplicative).  
2. Combat turn resolution includes a "Bleed/Consciousness Check" at the end of every round.  
3. The calculate\_defender\_value must check if the defender is "Petrified" or "Stunned," applying a Readiness \*= 0.01 penalty.