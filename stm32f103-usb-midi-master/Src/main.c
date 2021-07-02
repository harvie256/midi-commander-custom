/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * This notice applies to any and all portions of this file
  * that are not between comment pairs USER CODE BEGIN and
  * USER CODE END. Other portions of this file, whether 
  * inserted by the user or by software development tools
  * are owned by their respective copyright owners.
  *
  * Copyright (c) 2019 STMicroelectronics International N.V. 
  * All rights reserved.
  *
  * Redistribution and use in source and binary forms, with or without 
  * modification, are permitted, provided that the following conditions are met:
  *
  * 1. Redistribution of source code must retain the above copyright notice, 
  *    this list of conditions and the following disclaimer.
  * 2. Redistributions in binary form must reproduce the above copyright notice,
  *    this list of conditions and the following disclaimer in the documentation
  *    and/or other materials provided with the distribution.
  * 3. Neither the name of STMicroelectronics nor the names of other 
  *    contributors to this software may be used to endorse or promote products 
  *    derived from this software without specific written permission.
  * 4. This software, including modifications and/or derivative works of this 
  *    software, must execute solely and exclusively on microcontroller or
  *    microprocessor devices manufactured by or for STMicroelectronics.
  * 5. Redistribution and use of this software other than as permitted under 
  *    this license is void and will automatically terminate your rights under 
  *    this license. 
  *
  * THIS SOFTWARE IS PROVIDED BY STMICROELECTRONICS AND CONTRIBUTORS "AS IS" 
  * AND ANY EXPRESS, IMPLIED OR STATUTORY WARRANTIES, INCLUDING, BUT NOT 
  * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
  * PARTICULAR PURPOSE AND NON-INFRINGEMENT OF THIRD PARTY INTELLECTUAL PROPERTY
  * RIGHTS ARE DISCLAIMED TO THE FULLEST EXTENT PERMITTED BY LAW. IN NO EVENT 
  * SHALL STMICROELECTRONICS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, 
  * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF 
  * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
  * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
  * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "spi.h"
#include "tim.h"
#include "usb_device.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "usbd_midi_if.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
/* Private variables ---------------------------------------------------------*/
uint8_t Hold_On[4] = {0x08, 0x90, 0x40, 0x47};
 uint8_t Hold_Off[4] = {0x08, 0x80, 0x40, 0x47};
 uint8_t Hold = 0;

 uint8_t Time_On[4] = {0x08, 0x90, 0x41, 0x47};
 uint8_t Time_Off[4] = {0x08, 0x80, 0x41, 0x47};
 uint8_t Time = 0;

 uint8_t Eject_On[4] = {0x08, 0x90, 0x42, 0x47};
 uint8_t Eject_Off[4] = {0x08, 0x80, 0x42, 0x47};
 uint8_t Eject = 0;

 uint8_t MasterTempo_On[4] = {0x08, 0x90, 0x43, 0x47};
 uint8_t MasterTempo_Off[4] = {0x08, 0x80, 0x43, 0x47};
 uint8_t MasterTempo = 0;

 uint8_t TrackBack_On[4] = {0x08, 0x90, 0x44, 0x47};
 uint8_t TrackBack_Off[4] = {0x08, 0x80, 0x44, 0x47};
 uint8_t TrackBack = 0;

 uint8_t TrackForward_On[4] = {0x08, 0x90, 0x45, 0x47};
 uint8_t TrackForward_Off[4] = {0x08, 0x80, 0x45, 0x47};
 uint8_t TrackForward = 0;

 uint8_t Jet_On[4] = {0x08, 0x90, 0x46, 0x47};
 uint8_t Jet_Off[4] = {0x08, 0x80, 0x46, 0x47};
 uint8_t Jet = 0;

 uint8_t Zip_On[4] = {0x08, 0x90, 0x47, 0x47};
 uint8_t Zip_Off[4] = {0x08, 0x80, 0x47, 0x47};
 uint8_t Zip = 0;

 uint8_t Wah_On[4] = {0x08, 0x90, 0x48, 0x47};
 uint8_t Wah_Off[4] = {0x08, 0x80, 0x48, 0x47};
 uint8_t Wah = 0;

 uint8_t Play_On[4] = {0x08, 0x90, 0x49, 0x47};
 uint8_t Play_Off[4] = {0x08, 0x80, 0x49, 0x47};
 uint8_t Play = 0;

 uint8_t Cue_On[4] = {0x08, 0x90, 0x4A, 0x47};
 uint8_t Cue_Off[4] = {0x08, 0x80, 0x4A, 0x47};
 uint8_t Cue = 0;

 uint8_t ScanBack_On[4] = {0x08, 0x90, 0x4B, 0x47};
 uint8_t ScanBack_Off[4] = {0x08, 0x80, 0x4B, 0x47};
 uint8_t ScanBack = 0;

 uint8_t ScanForward_On[4] = {0x08, 0x90, 0x4C, 0x47};
 uint8_t ScanForward_Off[4] = {0x08, 0x80, 0x4C, 0x47};
 uint8_t ScanForward = 0;

 uint8_t JogForward[4] = {0x08, 0xB0, 0x24, 0x01};
 uint8_t JogBack[4] = {0x08, 0xB0, 0x24, 0x7F};
 volatile uint8_t Jog = 0;
 volatile uint8_t Pulse = 0;

 uint8_t Pitch[4] = {0x08, 0xE0, 0x00, 0x00};
 uint16_t pitch = 0, pitch_prev = 0;
 uint16_t adc_data[2] = {0};

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
/* Private function prototypes -----------------------------------------------*/

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USB_DEVICE_Init();
  MX_ADC1_Init();
  MX_SPI1_Init();
  MX_TIM4_Init();
  MX_TIM1_Init();
  /* USER CODE BEGIN 2 */
  HAL_Delay(1000);
  HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&adc_data, 2);
  HAL_TIM_Base_Start_IT(&htim1);
  HAL_TIM_OC_Start_IT(&htim1, TIM_CHANNEL_1);
  HAL_TIM_Encoder_Start_IT(&htim4, TIM_CHANNEL_1 | TIM_CHANNEL_2);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  HAL_GPIO_WritePin(S1_GPIO_Port, S1_Pin, GPIO_PIN_SET);
	  if(HAL_GPIO_ReadPin(KD0_GPIO_Port, KD0_Pin) == GPIO_PIN_SET) {
		  if(Hold == 0) {
			  Hold = 1;
			  MIDI_DataTx(Hold_On, 4);
		  }
	  }
	  else {
		  if(Hold == 1) {
			  Hold = 0;
			  MIDI_DataTx(Hold_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD1_GPIO_Port, KD1_Pin) == GPIO_PIN_SET) {
		  if(TrackBack == 0) {
			  TrackBack = 1;
			  MIDI_DataTx(TrackBack_On, 4);
		  }
	  }
	  else {
		  if(TrackBack == 1) {
			  TrackBack = 0;
			  MIDI_DataTx(TrackBack_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD2_GPIO_Port, KD2_Pin) == GPIO_PIN_SET) {
		  if(Play == 0) {
			  Play = 1;
			  MIDI_DataTx(Play_On, 4);
		  }
	  }
	  else {
		  if(Play == 1) {
			  Play = 0;
			  MIDI_DataTx(Play_Off, 4);
		  }
	  }
	  HAL_GPIO_WritePin(S1_GPIO_Port, S1_Pin, GPIO_PIN_RESET);
	  HAL_GPIO_WritePin(S2_GPIO_Port, S2_Pin, GPIO_PIN_SET);
	  if(HAL_GPIO_ReadPin(KD0_GPIO_Port, KD0_Pin) == GPIO_PIN_SET) {
		  if(Time == 0) {
			  Time = 1;
			  MIDI_DataTx(Time_On, 4);
		  }
	  }
	  else {
		  if(Time == 1) {
			  Time = 0;
			  MIDI_DataTx(Time_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD1_GPIO_Port, KD1_Pin) == GPIO_PIN_SET) {
		  if(TrackForward == 0) {
			  TrackForward = 1;
			  MIDI_DataTx(TrackForward_On, 4);
		  }
	  }
	  else {
		  if(TrackForward == 1) {
			  TrackForward = 0;
			  MIDI_DataTx(TrackForward_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD2_GPIO_Port, KD2_Pin) == GPIO_PIN_SET) {
		  if(Cue == 0) {
			  Cue = 1;
			  MIDI_DataTx(Cue_On, 4);
		  }
	  }
	  else {
		  if(Cue == 1) {
			  Cue = 0;
			  MIDI_DataTx(Cue_Off, 4);
		  }
	  }
	  HAL_GPIO_WritePin(S2_GPIO_Port, S2_Pin, GPIO_PIN_RESET);
	  HAL_GPIO_WritePin(S3_GPIO_Port, S3_Pin, GPIO_PIN_SET);
	  if(HAL_GPIO_ReadPin(KD0_GPIO_Port, KD0_Pin) == GPIO_PIN_SET) {
		  if(Eject == 0) {
			  Eject = 1;
			  MIDI_DataTx(Eject_On, 4);
		  }
	  }
	  else {
		  if(Eject == 1) {
			  Eject = 0;
			  MIDI_DataTx(Eject_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD1_GPIO_Port, KD1_Pin) == GPIO_PIN_SET) {
		  if(Jet == 0) {
			  Jet = 1;
			  MIDI_DataTx(Jet_On, 4);
		  }
	  }
	  else {
		  if(Jet == 1) {
			  Jet = 0;
			  MIDI_DataTx(Jet_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD2_GPIO_Port, KD2_Pin) == GPIO_PIN_SET) {
		  if(ScanBack == 0) {
			  ScanBack = 1;
			  MIDI_DataTx(ScanBack_On, 4);
		  }
	  }
	  else {
		  if(ScanBack == 1) {
			  ScanBack = 0;
			  MIDI_DataTx(ScanBack_Off, 4);
		  }
	  }
	  HAL_GPIO_WritePin(S3_GPIO_Port, S3_Pin, GPIO_PIN_RESET);
	  HAL_GPIO_WritePin(S4_GPIO_Port, S4_Pin, GPIO_PIN_SET);
	  if(HAL_GPIO_ReadPin(KD0_GPIO_Port, KD0_Pin) == GPIO_PIN_SET) {
		  if(MasterTempo == 0) {
			  MasterTempo = 1;
			  MIDI_DataTx(MasterTempo_On, 4);
		  }
	  }
	  else {
		  if(MasterTempo == 1) {
			  MasterTempo = 0;
			  MIDI_DataTx(MasterTempo_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD1_GPIO_Port, KD1_Pin) == GPIO_PIN_SET) {
		  if(Zip == 0) {
			  Zip = 1;
			  MIDI_DataTx(Zip_On, 4);
		  }
	  }
	  else {
		  if(Zip == 1) {
			  Zip = 0;
			  MIDI_DataTx(Zip_Off, 4);
		  }
	  }
	  if(HAL_GPIO_ReadPin(KD2_GPIO_Port, KD2_Pin) == GPIO_PIN_SET) {
		  if(ScanForward == 0) {
			  ScanForward = 1;
			  MIDI_DataTx(ScanForward_On, 4);
		  }
	  }
	  else {
		  if(ScanForward == 1) {
			  ScanForward = 0;
			  MIDI_DataTx(ScanForward_Off, 4);
		  }
	  }
	  HAL_GPIO_WritePin(S4_GPIO_Port, S4_Pin, GPIO_PIN_RESET);
	  HAL_GPIO_WritePin(S5_GPIO_Port, S5_Pin, GPIO_PIN_SET);
	  if(HAL_GPIO_ReadPin(KD1_GPIO_Port, KD1_Pin) == GPIO_PIN_SET) {
		  if(Wah == 0) {
			  Wah = 1;
			  MIDI_DataTx(Wah_On, 4);
		  }
	  }
	  else {
		  if(Wah == 1) {
			  Wah = 0;
			  MIDI_DataTx(Wah_Off, 4);
		  }
	  }
	  HAL_GPIO_WritePin(S5_GPIO_Port, S5_Pin, GPIO_PIN_RESET);
	  if(Pulse > 0) {
		  if(__HAL_TIM_IS_TIM_COUNTING_DOWN(&htim4) == 0) {
			  	  MIDI_DataTx(JogBack, 4);
		  }
		  else {
			    MIDI_DataTx(JogForward, 4);
		  }
		  Pulse--;
	  }
	  uint16_t pitch = 0x2000 * adc_data[0] / adc_data[1];
	  if(abs(pitch - pitch_prev) > 100) {
		  Pitch[2] = pitch % 128;
		  Pitch[3] = pitch / 128;
		  MIDI_DataTx(Pitch, 4);
		  pitch_prev = pitch;
	  }
	  HAL_Delay(10);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /**Initializes the CPU, AHB and APB busses clocks 
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL12;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /**Initializes the CPU, AHB and APB busses clocks 
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_1) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC|RCC_PERIPHCLK_USB;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV4;
  PeriphClkInit.UsbClockSelection = RCC_USBCLKSOURCE_PLL;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  while(1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{ 
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     tex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
