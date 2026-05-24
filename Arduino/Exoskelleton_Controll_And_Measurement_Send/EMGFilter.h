// Based on the code by OYMotion's EMG Filter
// taken from: https://github.com/YeezB/EMG_Filter
#ifndef _EMGFILTER_H
#define _EMGFILTER_H

enum NOTCH_FREQUENCY { NOTCH_FREQ_50HZ = 50, NOTCH_FREQ_60HZ = 60 };
enum SAMPLE_FREQUENCY { SAMPLE_FREQ_500HZ = 500, SAMPLE_FREQ_1000HZ = 1000 };
enum FILTER_TYPE { FILTER_TYPE_LOWPASS = 0, FILTER_TYPE_HIGHPASS };

// Moved to header so each instance can have its own state variables
class FILTER_2nd {
  private:
    float states[2];
    float num[3];
    float den[3];
  public:
    void init(FILTER_TYPE ftype, int sampleFreq);
    float update(float input);
};

class FILTER_4th {
  private:
    float states[4];
    float num[6];
    float den[6];
    float gain;
  public:
    void init(int sampleFreq, int humFreq);
    float update(float input);
};

class EMGFilters {
  public:
    void init(SAMPLE_FREQUENCY sampleFreq,
              NOTCH_FREQUENCY  notchFreq,
              bool             enableNotchFilter    = true,
              bool             enableLowpassFilter  = true,
              bool             enableHighpassFilter = true);

    int update(int inputValue);

  private:
    SAMPLE_FREQUENCY m_sampleFreq;
    NOTCH_FREQUENCY  m_notchFreq;
    bool             m_bypassEnabled;
    bool             m_notchFilterEnabled;
    bool             m_lowpassFilterEnabled;
    bool             m_highpassFilterEnabled;

    // These are now unique to each EMGFilters instance!
    FILTER_2nd LPF;
    FILTER_2nd HPF;
    FILTER_4th AHF;
};

#endif