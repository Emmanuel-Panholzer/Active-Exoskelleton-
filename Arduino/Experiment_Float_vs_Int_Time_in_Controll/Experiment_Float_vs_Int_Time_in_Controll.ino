// --- BENCHMARK SETTINGS ---
const int ITERATIONS = 10000;


volatile int val1 = 150;
volatile int val2 = 50;

const float WAIGHTING_FACTOR_F = 1.1;
const float THRESHOLD_F = 20.0;
const float SPEED_MULTIPLIER_F = 0.2;
const float EASING_FACTOR_F = 0.15;

const long WAIGHT_NUM = 11;   
const long WAIGHT_DEN = 10;   
const long SPEED_NUM = 2;    
const long SPEED_DEN = 10;    
const long EASING_NUM = 15;  
const long EASING_DEN = 100;  
const long THRESHOLD_I = 20;
const long ANGLE_SCALE = 1000;

void setup() {
  Serial.begin(2000000);
  delay(2000);

  Serial.println("Starting Benchmark (10,000 Iterations)...");
  Serial.println("-----------------------------------------");

  // ========================================================
  // 1. FLOAT MATH TEST
  // ========================================================
  float targetAngleFloat = 90.0;
  float currentAngleFloat = 90.0;
  volatile int microSecFloat = 1500;

  unsigned long startFloat = micros();

  for (int i = 0; i < ITERATIONS; i++) {
    int bic = val1 + (i % 10); 
    int tri = val2 + (i % 5);

    float angleChange = 0;
    float val = bic - (tri * WAIGHTING_FACTOR_F);

    if (abs(val) >= THRESHOLD_F) {
      if (val > 0) val -= THRESHOLD_F;
      else if (val < 0) val += THRESHOLD_F;
      angleChange += val * SPEED_MULTIPLIER_F;
    }

    if (angleChange != 0) {
      targetAngleFloat += angleChange;
      targetAngleFloat = constrain(targetAngleFloat, 0.0, 180.0);
      currentAngleFloat += (targetAngleFloat - currentAngleFloat) * EASING_FACTOR_F;
      microSecFloat = 500 + (currentAngleFloat / 180.0) * (2400.0 - 500.0);
    }
  }

  unsigned long timeFloat = micros() - startFloat;

  // ========================================================
  // 2. INTEGER MATH TEST
  // ========================================================
  long targetAngleInt = 90 * ANGLE_SCALE;  // 90000
  long currentAngleInt = 90 * ANGLE_SCALE; // 90000
  volatile int microSecInt = 1500;

  unsigned long startInt = micros();

  for (int i = 0; i < ITERATIONS; i++) {
    int bic = val1 + (i % 10);
    int tri = val2 + (i % 5);

    long angleChangeInt = 0;
    long val = bic - ((tri * WAIGHT_NUM) / WAIGHT_DEN);

    if (abs(val) >= THRESHOLD_I) {
      if (val > 0) val -= THRESHOLD_I;
      else if (val < 0) val += THRESHOLD_I;
      angleChangeInt = (val * SPEED_NUM * ANGLE_SCALE) / SPEED_DEN; 
    }

    if (angleChangeInt != 0) {
      targetAngleInt += angleChangeInt;
      
      // Integer Constrain
      if (targetAngleInt < 0) targetAngleInt = 0;
      if (targetAngleInt > 180 * ANGLE_SCALE) targetAngleInt = 180 * ANGLE_SCALE;

      // Integer Easing
      currentAngleInt += ((targetAngleInt - currentAngleInt) * EASING_NUM) / EASING_DEN;
      
      // Integer Microsecond Calculation: 500 + (Angle/1800) * (2400 - 500) / ANGLE_SCALE
      microSecInt = 500 + (currentAngleInt / 180) * (2400 - 500) / ANGLE_SCALE; 
    }
  }

  unsigned long timeInt = micros() - startInt;

  // ========================================================
  // 3. PRINT RESULTS
  // ========================================================
  Serial.print("Float Math Time:   "); 
  Serial.print(timeFloat); 
  Serial.println(" microseconds");

  Serial.print("Integer Math Time: "); 
  Serial.print(timeInt); 
  Serial.println(" microseconds");

  Serial.println("-----------------------------------------");
  Serial.print("Final Float output: "); Serial.println(microSecFloat);
  Serial.print("Final Int output:   "); Serial.println(microSecInt);
}

void loop() {
  // Do nothing
}